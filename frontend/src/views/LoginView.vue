<script>
import LoginForm from '../components/LoginForm.vue'
export default {
	components: { LoginForm },

	methods: {
		onLoginClicked(value) {
			console.log(value)
		}
	}
}

</script>


<template>
	<div class="split left">
		<h3> Heat Variant </h3>
		<br><br>
		<LoginForm @clicked="onLoginClicked" />
	</div>
	<div class="split right">
		<!-- Rightie -->
	</div>
</template>


<style>
h3 {
	font-size: 30px;
	color: #7FA494
}

.split {
	height: 100%;
	width: 50%;
	position: fixed;
	z-index: 1;
	top: 0;
	overflow-x: hidden;
	padding-top: 20px;
}

.left {
	padding-left: 20px;
	padding-right: 20px;
	left: 0;
	width: 50%;
	background-color: whitesmoke;
	color: #7FA494;
}

.right {
	width: 50%;
	background-color: #7FA494;
	color: whitesmoke;
	font-size: 20px;
}

/* 
.row:after {
	content: "";
	display: table;
	clear: both;
} */

* {
	padding: 0;
	margin: 0;
}
</style>